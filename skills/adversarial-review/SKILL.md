---
name: adversarial-review
description: >
  Revisión ADVERSARIAL de un diff con lentes de contexto fresco en paralelo — A (conformidad con
  spec/plan/constitución, veredicto por criterio ✓/✗), B (solo defectos de corrección) y C
  (seguridad, CONDICIONAL: solo si `review-lens-select.py` detecta ficheros o líneas sensibles en
  el diff) — con fusión, graduación Critical/Important/Minor, bucle acotado a 3 intentos, rebate
  con evidencia y traza en el ledger («Revisión de dos lentes — intento N»). Fuente única del
  método que usan /dev-cycle (Fase 3) y quick-implement; también a demanda sobre una rama o rango
  sin ledger. NO sustituye a `qa` (E2E + qa-gate) ni a `nemesis` (auditoría de seguridad
  completa), y NO revisa estilo ni propone refactors. Úsala cuando el usuario diga "revisa este
  diff", "revisión adversarial", "pasa las dos lentes", "revisión de dos lentes", "busca gaps en
  la rama", o cuando /dev-cycle o quick-implement lleguen a la puerta de revisión.
---

# adversarial-review — dos lentes (+ una condicional) contra el diff, con bucle acotado

Patrón que más críticos reales ha cazado en este repo (ver `docs/knowledge/lessons/LES-010-*`):
revisores de **contexto fresco** que NO han visto implementar, cada uno con una lente distinta,
sobre el **diff** y no sobre el repo entero. Esta skill es la **fuente única del método**: los
orquestadores (`/dev-cycle`, `quick-implement`) la invocan por nombre y conservan solo lo suyo
(contador de intentos, decisión al 3.º, imputación de horas).

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

```bash
python3 "$SHAREDKIT/scope-check.py" "docs/roadmap/<fecha>-<slug>"      # exit 0 obligatorio para lanzar las lentes
```

Compara los ficheros cambiados (comiteados + sin comitear) con los campos `Archivos` de TODAS las
tareas del ledger (`tasks.md` propio y `docs/knowledge/**` siempre en alcance). **Exit 1** → los
ficheros fuera de alcance vuelven al `implementer` como **gap Important** ANTES de lanzar las
lentes: o revierte el cambio, o justifica que es necesario — entonces se añade al campo `Archivos`
de su tarea con una nota y se relanza el check. **Exit 2** (sin base clara: ni `main` ni `master`)
→ pásale `--base <ref>`. Sin git → salta la puerta con aviso (la Lente A conserva su comprobación
(2) como red).

### 1. ¿Aplica la Lente C? (determinista)

```bash
python3 "$REVSKILL/scripts/review-lens-select.py" [--base <ref>] [--json]   # exit 0 siempre
```

Devuelve `lente_c: true|false` + motivos (fichero + patrón). Heurística por **RUTA** (stems anclados
al inicio de un token de la ruta y, los que son prefijo de palabras inocuas, con límite final:
`auth(?!or)`, login, session(s), token(s)¹, oauth, jwt, password, secret(s), crypt, permission(s),
acl¹, rbac¹, cors¹, csrf, upload, payment, billing, docker, nginx, k8s, helm¹; más `.env*`,
`Dockerfile*` y `.github/workflows/` — `authz.py`/`session-context.sh`/`tokens.py`/`token_store.py`
sí; `oracle.py`/`tokenizer.py`/`helmet.py`/`author.md` no (¹ = con límite `(?![a-z])`); la prosa
`.md/.txt/.rst` y `docs/**` no se evalúan por ruta, `tests/**` sí; `"revision": {"excluir": ["hooks/**"]}`
en `dev.json` saca globs de la heurística de ruta —para un repo cuyos hooks se llamen `session-*.sh`—
**sin** sacarlos del escaneo de contenido) y por **CONTENIDO de las
líneas añadidas** del diff (las borradas no cuentan): `eval(`/`exec(`, `subprocess` **solo con
`shell=True` en la misma línea**, `os.system(`/`os.popen(`, `innerHTML`/`dangerouslySetInnerHTML`,
`pickle.loads(`, `yaml.load(`, SQL concatenado o en f-string, `API_KEY`, `PRIVATE KEY`/`BEGIN RSA`,
`Authorization:`, `Set-Cookie`. La prosa, `docs/**`, los tests y las fixtures no se escanean por
contenido (contienen payloads a propósito); los binarios se saltan. Configurable en
`.claude/dev.json` → `"revision": {"lenteSeguridad": "auto" | "siempre" | "nunca", "excluir": ["glob", …]}`
(default `auto`, sin exclusiones; `/setup` paso 5-ter pregunta el modo; `excluir` es ajuste manual).
El script nunca bloquea: ante error avisa por stderr y devuelve `false`. La lista exacta de patrones
es el contrato: `CONTENIDO`/`RUTA_RE` en el propio script, con sus tests.

### 2. Lanzar las lentes en PARALELO (subagentes genéricos, contexto limpio, que NO hayan visto implementar)

Cada lente recibe SOLO: el diff (o cómo obtenerlo), las rutas de los artefactos contra los que
revisa, y si N > 1 la tabla del intento anterior (ver §5). Prompts literales:

- **Lente A — conformidad con la spec/plan (y la constitución si existe):** "Revisa el diff de la iniciativa `docs/roadmap/<fecha>-<slug>/` contra `improvement-plan.md` y `tasks.md`. Comprueba: (1) cada `T-XX` marcada como hecha está realmente implementada y cumple sus criterios; (2) nada fuera del alcance del plan (`scope-check.py` acaba de pasar; confirma que lo declarado en `Archivos` es lo que el plan pedía); (3) los criterios con test tienen su test; (4) **si existe `docs/CONSTITUTION.md`**, ningún cambio viola un principio EXPLÍCITO del fichero — si lo viola, es gap de corrección **citando la línea del principio**; lo que no esté escrito ahí es estilo, no gap (no inventes principios). **Devuelve salida ESTRUCTURADA por criterio: `T-XX` → cada criterio de aceptación → ✓/✗**, más los gaps (fichero:línea). Solo gaps de requisitos/constitución, no estilo."
  *Modo sin plan:* sustituye «contra `improvement-plan.md` y `tasks.md`» por «contra el objetivo declarado: <objetivo> y los mensajes de commit del rango `<base>..HEAD`», y (1)-(3) por «cada objetivo/commit hace lo que dice y nada más; lo que cambia y no lo explica ningún commit es gap».
- **Lente B — calidad y robustez del código:** "Revisa el diff de la iniciativa buscando SOLO defectos de corrección: casos límite sin manejar, errores silenciados, condiciones de carrera, inputs que rompen, regresiones probables. NO reportes preferencias de estilo ni sugerencias de refactor. Lista de defectos (fichero:línea, escenario concreto de fallo) o 'sin defectos'."
  *Persona de dominio:* si la tarea (o la mayoría de las tareas del diff) lleva `- **Tipo**: frontend|backend|db|devops|test|docs`, antepón al prompt el perfil corto de `"$SHAREDKIT/personas/<tipo>.md"` (misma mecánica que `task-brief.py`: prioridades, trampas típicas y evidencia exigible del dominio). Sin etiqueta o sin perfil en el catálogo → lente genérica, nunca bloquea.
- **Lente C — seguridad del diff (SOLO si `lente_c: true`):** "Contexto fresco. Revisa SOLO el diff `<base>..HEAD` buscando vulnerabilidades introducidas o reabiertas: inyección (SQL/comando/plantilla), autenticación y sesión, secretos hardcodeados, deserialización insegura, path traversal, SSRF, permisos/autorización. Cita el CWE cuando aplique. NO hagas una auditoría completa del proyecto (eso es `nemesis`): solo lo que este diff introduce o reabre. Devuelve defectos con fichero:línea + escenario de explotación concreto, o 'sin hallazgos'. Motivos que activaron esta lente: <salida de review-lens-select>."
  Referencias que puede consultar (solo las listas, NO la skill `cybersecurity` entera —976 líneas—): `skills/cybersecurity/references/vulnerability-taxonomy.md` (OWASP/CWE unificado), `skills/cybersecurity/references/language-patterns/<lenguaje>.md` (patrones peligrosos por lenguaje), `skills/cybersecurity/references/iac-patterns/{dockerfile,github-actions,kubernetes,terraform}.md` si el diff toca IaC, y `skills/cybersecurity/references/false-positive-suppression.md` para no reportar lo que el framework ya mitiga. Resuélvelas con `find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/cybersecurity/references/…'`; si no están instaladas, la lente corre con su propio criterio y lo dice.

### 3. Fusionar y graduar

**Fusiona** las 2-3 salidas: deduplica gaps que señalen lo mismo (mismo `fichero:línea` o mismo
escenario); la Lente A da el **veredicto por criterio** (✓/✗); B y C aportan defectos a la lista de
gaps (los de C llevan su CWE). Gradúa cada gap **`Critical / Important / Minor`**: Critical
(pérdida de datos, seguridad explotable, criterio de aceptación incumplido que rompe el objetivo)
e Important (defecto real reproducible, fuera de alcance, constitución violada) **obligan
corrección**; Minor se anota en el ledger sin bloquear el cierre.

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

### 6. Salida y traza

- **Siempre:** tabla por criterio (u objetivo) ✓/✗ + lista de gaps graduados con `fichero:línea`,
  escenario y veredicto (`corregido` · `descartado (rebatido)` · `deuda aceptada` · `pendiente`),
  y qué lentes corrieron (A+B, o A+B+C con los motivos).
- **Con ledger, además:** sección **`## Revisión de dos lentes — intento N: …`** al final de
  `tasks.md` (tabla `# · Grado · Gap · Tarea · Corrección · Evidencia`; ver
  `docs/roadmap/2026-09-02-deterministic-guardrails/tasks.md` como referencia de formato) y, al
  cerrar el bucle **sin gaps de corrección pendientes** (0 gaps, todos rebatidos con evidencia, o
  aceptados como deuda por el usuario), **promoción** de las entradas `docs/knowledge/` que la
  iniciativa escribió con `estado: propuesta` → `estado: aceptada (validada: revisión de dos
  lentes, AAAA-MM-DD, intento N)` (formato único de `"$SHAREDKIT/knowledge-write.md"` §Autoría).
  Si el 3.º intento sigue con gaps sin resolver, quedan en `propuesta`. `ledger-lint.py` exit 0
  tras escribir.
- **Jira (solo si `.claude/jira.json` `enabled` Y el plan se volcó):** el comentario es único y
  FINAL tras el bucle — Paso 9 de la skill `jira-sync`, renderizado contra
  `"$SHAREDKIT/review-report.template.md"` con la granularidad del volcado, incluyendo "revisión
  superada en N intento(s)"; idempotente (`reviewComentado`). El **worklog** `[revisión]` por
  intento lo imputa el orquestador (es contabilidad del ciclo, no del método).
- **Mensaje final al orquestador:** disciplina de `"$SHAREDKIT/output-discipline.md"` (≤ ~12
  líneas: veredicto, nº de gaps por grado, lentes que corrieron, ruta del ledger actualizado,
  siguiente paso). El detalle vive en el ledger.

> **Compatibilidad de la etiqueta.** El nombre de la sección en los ledgers y del promotor en
> `docs/knowledge/` sigue siendo **«Revisión de dos lentes»** aunque haya corrido la Lente C —
> `/retro`, `knowledge-write.md` y los dashboards lo buscan literal. La lente C es opcional y no
> cambia la etiqueta; anótala en el texto de la sección ("lentes: A+B+C").

## Scripts propios

- `scripts/review-lens-select.py` — decide si aplica la Lente C (heurística ruta+contenido sobre
  las líneas añadidas del diff; `dev.json` `revision.lenteSeguridad`); determinista, tests junto al
  script (`pytest -q skills/adversarial-review/scripts`), **exit 0 siempre** (error → aviso stderr +
  `lente_c: false`).
- Reutiliza sin duplicar: `agent-kits/shared/scope-check.py` (puerta), `ledger-lint.py`,
  `personas/`, `knowledge-write.md`, `review-report.template.md`, `output-discipline.md`.

## Qué NO hace

- No implementa ni corrige: devuelve gaps; corrige el `implementer` (o quien pidió la revisión).
- No da el verde de pruebas (`qa`/`qa-gate.py`) ni audita seguridad completa (`nemesis`).
- No toca `docs/roadmap/` salvo la sección de revisión del `tasks.md` de la iniciativa, ni
  `docs/knowledge/` salvo el campo `estado` de las entradas que promueve.
- No imputa horas: el worklog `[revisión]` por intento es del orquestador (`/dev-cycle`).
- No decide qué hacer al 3.º intento con gaps: lo devuelve al orquestador/usuario.

## Degradación

Sin `scope-check.py` o sin git → puerta saltada con aviso. Sin `review-lens-select.py` → solo A+B
(dilo). Sin `skills/cybersecurity/references/` → la Lente C corre con criterio propio y lo anota.
Sin `personas/` → Lente B genérica. Sin Jira activo → nada se publica. Nada de esto bloquea la
revisión; lo único obligatorio es el bucle acotado y la traza en el ledger cuando hay ledger.
