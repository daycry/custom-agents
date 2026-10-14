# Arreglo de build, revisión, desarrollo guiado y arnés GAN — C003, C005, C020, C024

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **15.295 bytes/507 líneas**. [commands-c1-cycle-review-reading-evidence.json](commands-c1-cycle-review-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Contraste oficial: referencia de comandos de Claude Code
(<https://code.claude.com/docs/en/commands>, consultada el 2026-10-14): `/code-review`
es una skill incluida en el runtime (alias `/review`), con `--comment` para publicar
en el PR, y `/security-review` revisa la rama contra la rama por defecto.

**Decisiones previas que se respetan.** Los agentes que despachan estos comandos ya
están comparados: resolutores de build en
[agents-build-resolvers-core.md](agents-build-resolvers-core.md) (línea común
integrada en `agents/implementer.md:90` y `skills/debug-root-cause/SKILL.md:106-108`);
`code-reviewer` (A008) en [agents-review-cpp-csharp-db.md](agents-review-cpp-csharp-db.md)
(línea de Lente B integrada en `references/lens-prompts.md:21`); `code-architect`
y `code-explorer` (A006, A007) en [agents-a11y-architect-explorer.md](agents-a11y-architect-explorer.md);
el arnés GAN (A025–A027) en [agents-gan-harness.md](agents-gan-harness.md) y la skill S111
en `skills-fsharp-gan-gateguard.md:24-42`. La fila «Revisión reproducible» de
[commands-workflow-comparison.md](commands-workflow-comparison.md) fija base/head
y publicación separada de la revisión local. Aquí solo va lo propio de cada comando.

## C003 — build-fix

`2.423 bytes/66 líneas` · tools/model: no declara. Detecta el build por el fichero
de proyecto, agrupa errores y los arregla uno a uno con Edit, recompilando cada vez.

- **Artefactos:** código del proyecto. **Dueño propio:** `implementer`, único que
  toca código (`docs/agents/ROLES.md:31`), con cambio mínimo y la línea de
  build roto (`agents/implementer.md:89-90`); al tercer rojo, `debug-root-cause`.
- **Despacho:** ninguno; el modelo principal edita sin ledger ni `Verificación`.
- **Disparador:** «el build está roto, arréglalo».
- **Escenario +:** dentro de una iniciativa → `implementer` P3; fuera de ella y
  acotado → `quick-implement` (vía rápida con ledger ligero y revisión).
- **Escenario −:** «sube la versión de X para que compile» → `dependency-upgrade`
  prepara la iniciativa; no la arregla `implementer` sobre la marcha.

**Comparación.** Sus paradas (42-46: más errores de los que arregla, tres
intentos, cambio de arquitectura, dependencias ausentes) coinciden con las
propias. Defectos: la tabla de detección propone `npx tsc --noEmit` (16), que
descarga el paquete del registro si no está instalado, contra su propia parada
por dependencias ausentes (46); y para Python ofrece `compileall -q .` **o**
`mypy .` (21), que no son equivalentes (el primero recorre también un `.venv`
dentro del árbol; el segundo es comprobación de tipos, no build).

**Destino:** **ya integrado** (línea común de los resolutores). Sin destino nuevo.

## C005 — code-review

`8.337 bytes/289 líneas` · `argument-hint: [pr-number | pr-url | blank]` · tools/model:
no declara. Dos modos: cambios locales sin comitear y PR de GitHub con validación
y publicación de la revisión.

- **Artefactos:** `.claude/reviews/pr-<N>-review.md` (191) y la revisión publicada
  en GitHub con `gh pr review --approve|--request-changes|--comment` y comentarios
  en línea (231-262). **Dueño propio:** la traza «Revisión de dos lentes — intento N»
  del ledger es de `adversarial-review` (`docs/agents/ROLES.md:39`); su único
  efecto externo es Jira opt-in (`SKILL.md:153-159`). **Publicar en GitHub no tiene
  dueño propio**: es un efecto externo y cae bajo «Efectos externos»
  (`skills/delivery-practices/references/delivery-tools.md:91-100`).
- **Despacho:** ninguno; el modelo principal revisa y ejecuta los comandos.
- **Disparador:** «revisa mis cambios», «revisa el PR 42».
- **Escenario +:** «revisa esta rama» → `adversarial-review` en modo sin plan
  (rama o rango + objetivo declarado, `SKILL.md:45`), lentes en `reviewer` de solo lectura.
- **Escenario −:** «audita la seguridad del repo» → `nemesis`; «repasa el estilo» → ninguna pieza (regla dura, `SKILL.md:23`, `:37`).

**Comparación.** Frente a A008 aporta los dos modos y la publicación. Defectos
propios del comando:

| Línea | Dice | Problema |
|---|---|---|
| 31 | Local: `git diff --name-only HEAD` | No ve ficheros nuevos sin seguimiento: un módulo recién creado queda sin revisar. `scope-check.py` sí los cuenta (`:12`, `:295`) |
| 110-114, 140-171 | Lee los ficheros del head del PR por la API, pero valida con `npm test`/`build` en el checkout local | La validación es de la rama local, no del PR; con ella decide APPROVE (179) sobre código que no ejecutó |
| 146 | `npx tsc --noEmit` | Puede descargar el paquete (igual que C003) |
| 52-59 | `console.log`, TODO, JSDoc ausente y emojis como HIGH/MEDIUM | Estilo; la regla dura propia lo excluye |
| 71 | «Block commit if CRITICAL or HIGH» | Sin mecanismo: es prosa |
| 187, 237 | `--approve` fuerza la decisión; publica la aprobación sin confirmar | Aprueba en nombre del usuario sin aprobación ligada al objeto; el veredicto publicado puede contradecir los hallazgos |

El nombre coincide con la skill nativa `/code-review`.

**Destino:** una línea en `skills/adversarial-review/SKILL.md`, tabla de modos,
fila «Sin plan»: «Si el rango es un PR remoto, revisa y ejecuta la evidencia
sobre el mismo commit (un worktree del head), nunca sobre la rama local. Publicar
el veredicto en el PR es un efecto externo (`delivery-tools.md`, «Efectos externos»):
se muestra y solo se publica con OK explícito del usuario, nunca como aprobación
automática». El resto queda cubierto.

## C020 — feature-dev

`1.282 bytes/49 líneas` · tools/model: no declara. Siete fases: descubrimiento,
exploración (`code-explorer`), preguntas, diseño (`code-architect`), implementación,
revisión (`code-reviewer`) y resumen.

- **Artefactos:** ninguno declarado. **Dueño propio de cada fase:** `analyst`
  (spec aprobada), `architect` (2-3 opciones y elección del usuario,
  `agents/architect.md:59`, `:158`), `planner`, `implementer`, `adversarial-review`
  y `qa`, secuenciados por `/dev-cycle` (`docs/agents/ROLES.md:38`). La exploración
  es un paso de cada rol (`agent-kits/shared/read-discipline.md`).
- **Despacho:** `code-explorer`, `code-architect`, `code-reviewer` (sin destino en sus fichas).
- **Disparador:** «desarrolla esta funcionalidad».
- **Escenario +:** «implementa la exportación a CSV y compara diseños antes» → `/dev-cycle` completo con `architect`; «añade este filtro» → `quick-implement`.
- **Escenario −:** «explícame cómo funciona el login» → no hay ciclo; respuesta directa leyendo el código.

**Comparación.** Sus dos puertas (preguntas tras explorar, 21-25; aprobación del
diseño antes de implementar, 31) ya están en `/dev-cycle` (Fase 0 pasos 3-4,
`:29-30`; puerta de `design.md`, `:91`). Le faltan presupuesto, ledger, `Verificación`,
QA, retro y alternativas de diseño; «prefer TDD where appropriate» (36) deja el
método a juicio, cuando el propio es opt-in con evidencia del rojo.

**Destino:** **Sin destino.** Duplicaría `/dev-cycle` (ADR-011).

## C024 — gan-build

`3.253 bytes/103 líneas` · tools/model: no declara. Orquesta `gan-planner` y un
bucle `gan-generator` ↔ `gan-evaluator` con nota ponderada.

- **Artefactos:** `gan-harness/spec.md`, `eval-rubric.md`, `feedback/*.md`,
  `build-report.md`. **Dueños propios:** `spec.md` es de `analyst` con aprobación
  del usuario; los criterios de aceptación, de `planner`; la crítica, de
  `adversarial-review` (traza en el ledger); la prueba del producto, de `qa`
  (`testing/`); el resumen final sale del ledger (`/dev-cycle` Fase 6 paso 3).
- **Despacho:** tres agentes por Task tool, hasta 15 iteraciones (7).
- **Disparador:** «constrúyelo e itera hasta que esté bien».
- **Escenario +:** esa petición → `/dev-cycle` completo, con bucles acotados a 3 (`:409`, `:413`) y verde de `qa-gate.py`.
- **Escenario −:** «itera hasta nota 7» → ninguna pieza propia acepta una nota del modelo como veredicto (`skills-destinations.md:390`).

**Comparación.** Además de lo ya decidido para sus agentes, el comando añade
defectos propios:

| Línea | Dice | Problema |
|---|---|---|
| 7, 61-63 | 15 iteraciones por defecto; parada por meseta de nota | Hasta 31 despachos (planificador + 15 × 2) sin tope de coste; la meseta compara notas ruidosas del modelo |
| 19 | «Initialize git if not already initialized» | Crea un repositorio en la carpeta del usuario sin preguntar |
| 40 | El generador hace commit en cada iteración | Sin rama declarada; el plugin bloquea escribir en `main` (`agents/implementer.md:62`) |
| 37, 49, 54 frente a 98 | `feedback-{iteration}.md` frente a `feedback-001.md` | Dos convenciones de nombre: el lector puede no encontrar el fichero |
| 55 | «Extract weighted total score» de la prosa | Sin formato fijado: el veredicto depende de parsear texto libre |
| 9 | `--skip-planner` asume que `spec.md` existe | No lo comprueba |
| 73, 99 | «estimated cost»; `generator-state.md` en la lista de ficheros | Ninguna fase mide coste ni escribe ese fichero |

**Destino:** **Sin destino** (S111 y A025–A027).

## Resumen

| ID | Dueño propio | Destino |
|---|---|---|
| C003 | `implementer` + `debug-root-cause` | Ya integrado (línea común) |
| C005 | `adversarial-review` + `reviewer` | Línea en `adversarial-review/SKILL.md` (PR remoto y publicación) |
| C020 | `/dev-cycle` | Sin destino |
| C024 | `/dev-cycle`, `qa-gate.py` | Sin destino |
